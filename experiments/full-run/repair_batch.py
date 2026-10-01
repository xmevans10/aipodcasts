#!/usr/bin/env python3
"""Salvage specific reviewed drafts instead of discarding their supported work.

Re-ingest primary evidence, give the writer the exact previous draft and reviewer spans,
and require fresh factual and audience approvals. Only explicitly selected hosts change.
"""
import argparse
import json
import shutil
from pathlib import Path

from run_all_shows import (HOSTS, approve_auto, connect, draft_story, ingest_any, load_local_env,
                           row, render, slug, word_count)
from check_batch import check_batch
from audience import repair_instructions


def candidate(seed: Path, host: str, excluded: set[str]) -> dict:
    paths = list((seed / 'withheld').glob('*.json'))
    approved = seed / 'transcripts' / (slug(HOSTS[host].show) + '.json')
    if approved.is_file(): paths.append(approved)
    eligible = []
    for path in paths:
        artifact = json.loads(path.read_text())
        if artifact.get('host') != host or artifact.get('doi', '').casefold() in excluded:
            continue
        verification = artifact.get('verification') or {}
        factual = verification.get('factual') or verification
        listener = artifact.get('audience') or {}
        if factual.get('pass') and listener.get('beat_fit') == 'grounded' and listener.get('decision') in ('pass', 'revise'):
            issues = sum((4 if i.get('rule') in ('numbers', 'limitations', 'result_concrete') else 1)
                         for i in listener.get('issues', []) if i.get('severity') in ('major', 'blocker'))
            eligible.append((issues, str(path), artifact))
    if not eligible:
        raise ValueError(f'{host}: no grounded, factually passing candidate available for repair')
    return min(eligible, key=lambda item: item[:2])[2]


def build(seed: Path, out: Path, hosts: list[str], excluded: set[str]):
    check_batch(seed, require_all=False)
    if not hosts or len(hosts) != len(set(hosts)) or any(h not in HOSTS for h in hosts):
        raise ValueError('Choose unique canonical hosts')
    manifest = json.loads((seed / 'manifest.json').read_text())
    if any(HOSTS[h].show not in {s['show'] for s in manifest['shows']} for h in hosts):
        raise ValueError('Host must be present in the seed manifest')
    if out.exists(): raise ValueError('Repair output must start fresh')
    selected = {host: candidate(seed, host, excluded) for host in hosts}
    shutil.copytree(seed, out)
    load_local_env(); db = connect()
    try:
        for host, previous in selected.items():
            stem = slug(HOSTS[host].show)
            # Selected scripts lose seed approval before any paid call. A failed rewrite
            # cannot silently leave the older version labeled as newly repaired.
            for ext in ('json', 'md'): (out / 'transcripts' / f'{stem}.{ext}').unlink(missing_ok=True)
            entry = next(e for e in manifest['shows'] if e['show'] == HOSTS[host].show)
            entry.update(status='repair_failed', verification_pass=False, audience_pass=False)
            try:
                story_id = ingest_any(db, previous['doi'], host, refresh=True)
                db.execute("UPDATE stories SET draft=?,state='review',reviewer=NULL,review_hash=NULL,audience_report=NULL WHERE id=?",
                           (json.dumps(previous['draft']), story_id)); db.commit()
                instructions = repair_instructions(previous.get('audience') or {})
                instructions += ('\nPreserve supported findings and the main limitation. '
                                 'Replace specialist labels with ordinary language instead of adding glossary paragraphs. '
                                 'Keep the hosts thinking and responding through the middle; do not turn the repair into a lecture. '
                                 'Rewrite technical source quotations in your own plain words. You may update the '
                                 'caveat field and its spoken passage together; verbatim matching does not require '
                                 'retaining the old wording or reading a source quotation aloud.')
                if host == 'yusuf':
                    instructions += ('\nThe current middle reads like a report. Let Yusuf reveal what he expected, '
                                     'which observed detail complicates it, and why that moves him. Remove the repeated '
                                     'sample counts in the limitation. Add no lived memory or facts.')
                draft_story(db, story_id, redraft=True, extra_instructions=instructions)
                verification = approve_auto(db, story_id, 'jev', repairs=1, factual_repairs=0)
                record = row(db, story_id); draft = json.loads(record['draft']); source = json.loads(record['source'])
                listener = verification.get('audience') or {}
                approved = verification.get('status') == 'approved'
                artifact = {**previous, 'story_id': story_id, 'draft': draft, 'words': word_count(draft),
                            'source': {k: source.get(k) for k in previous['source']},
                            'verification': verification, 'audience': listener,
                            'repairProvenance': {'previousDraft': previous['draft'],
                                                 'instructions': instructions, 'freshEvidenceIngested': True}}
                target = out / ('transcripts' if approved else 'withheld'); target.mkdir(exist_ok=True)
                filename = stem if approved else f'{stem}-{story_id}-repair'
                (target / f'{filename}.json').write_text(json.dumps(artifact, indent=2, ensure_ascii=False))
                (target / f'{filename}.md').write_text(render(draft, source, host))
                entry.update(status=verification['status'], doi=previous['doi'], title=draft['title'],
                             story_id=story_id, words=word_count(draft), evidence_tier=source.get('evidence_tier'),
                             verification_pass=verification.get('pass'), audience_pass=listener.get('pass'),
                             audience_decision=listener.get('decision'), beat_fit=listener.get('beat_fit'))
            except Exception as error:
                entry['errors'] = [f'{type(error).__name__}: {error}'[:200]]
            print(host, entry['status'], entry.get('title'), flush=True)
    finally:
        db.close()
        import datetime as dt
        manifest.update(generated=dt.datetime.now(dt.timezone.utc).isoformat(),
                        approved=sum(s['status'] == 'approved' for s in manifest['shows']))
        manifest['release_ready'] = manifest['approved'] == manifest['total']
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        (out / 'manifest.md').write_text(f"# Targeted repair\n\n{manifest['approved']}/{manifest['total']} strictly approved.\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--hosts', required=True)
    parser.add_argument('--exclude-dois-file', type=Path, required=True)
    args = parser.parse_args()
    build(args.seed_dir, args.out, args.hosts.split(','),
          {doi.casefold() for doi in json.loads(args.exclude_dois_file.read_text())})
