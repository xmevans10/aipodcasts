"""Pick up to three strictly reviewed episodes with contrasting hosts for private QA."""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiments/full-run'))
from check_batch import check_batch, slug


def select(batch: Path, out: Path, limit: int = 3) -> list[dict]:
    if not 1 <= limit <= 16:
        raise ValueError('QA episode limit must be between 1 and 16')
    check_batch(batch, require_all=False)
    entries = json.loads((batch / 'manifest.json').read_text())['shows']
    approved = [entry for entry in entries if entry.get('status') == 'approved']
    priority = ['atlas', 'fern', 'noor', 'jax', 'nova', 'yusuf', 'ines']
    approved.sort(key=lambda entry: (priority.index(entry['host'])
                                    if entry['host'] in priority else len(priority), entry['show']))
    if not approved:
        raise ValueError('No eligible scripts for audio QA')
    out.mkdir(parents=True, exist_ok=False)
    selected = approved[:limit]
    for entry in selected:
        for suffix in ('.json', '.md'):
            shutil.copyfile(batch / 'transcripts' / (slug(entry['show']) + suffix),
                            out / (slug(entry['show']) + suffix))
        print(f"QA: {entry['show']} — {entry['title']}")
    return selected


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--limit', type=int, default=3)
    args = parser.parse_args()
    select(args.batch, args.out, args.limit)
