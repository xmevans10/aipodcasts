"""Reproducible evidence-retention audit; optional paired API drafts, never publication.
Run from project root: python3 backend/evals/evaluate.py [--live]
The curated checklist is one-paper regression evidence, not an independent benchmark.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence import build_packet, evidence_text
from pipeline import load_local_env, connect, request, reserve_call, validate_draft, SCHEMA, HOSTS
from podcast import DEFAULT_MODEL, PODCAST_INSTRUCTIONS, validate_podcast

ROOT = Path(__file__).resolve().parent / 'leaf'

def audit():
    source = json.loads((ROOT / 'source.json').read_text())
    checks = json.loads((ROOT / 'checks.json').read_text())
    before = json.loads((ROOT / 'before.json').read_text())
    after = build_packet(source)
    (ROOT / 'after.json').write_text(json.dumps(after, ensure_ascii=False, indent=2))
    result = {'scope': 'Single-paper curated evidence availability, not model quality or semantic recall.',
              'source_characters': len(source['text']), 'versions': {}}
    for name, packet in [('before', before), ('after', after)]:
        selected = {p['id'] for p in packet['passages']}
        rows = [{**c, 'retained': bool(selected.intersection(c['evidence_ids']))} for c in checks]
        result['versions'][name] = {'characters': len(json.dumps(packet, ensure_ascii=False)),
            'paragraphs': len(selected), 'checks': rows,
            'retained': sum(c['retained'] for c in rows), 'total': len(rows),
            'core_retained': sum(c['retained'] for c in rows if c['priority'] == 'core'),
            'core_total': sum(c['priority'] == 'core' for c in rows)}
    (ROOT / 'audit.json').write_text(json.dumps(result, indent=2))
    return source, after, result


def paired_drafts(source, packet):
    load_local_env()
    key = os.environ.get('OPENAI_API_KEY')
    if not key: raise ValueError('OpenAI key missing: source audit completed; paired live drafts not run')
    model = os.environ.get('OPENAI_MODEL') or DEFAULT_MODEL
    instructions = PODCAST_INSTRUCTIONS + '\nHost delivery: ' + HOSTS['fern'][1]
    full = {'source_title': source['title'], 'source_attribution': source['attribution'],
            'source_journal': source.get('journal', ''),
            'scope': 'Complete extracted main-article text; no figure pixels or supplementary files.',
            'passages': [{'id': 'full', 'section': 'Full main-article text', 'text': source['text']}]}
    db = connect()
    try:
        for name, evidence in [('full', full), ('slim', packet)]:
            payload = {'model': model, 'store': False, 'instructions': instructions,
                       'input': json.dumps(evidence, ensure_ascii=False, separators=(',', ':')), 'max_output_tokens': 3500,
                       'text': {'format': {'type': 'json_schema', 'name': 'science_story', 'strict': True, 'schema': SCHEMA}}}
            if model.startswith('gpt-5.6-luna'): payload['reasoning'] = {'effort': os.environ.get('OPENAI_REASONING_EFFORT', 'low')}
            digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
            output = ROOT / f'{name}-{digest}.json'
            if output.exists():
                print(name + ': existing response reused'); continue
            call_id = reserve_call(db, 'openai', 'eval-leaf-' + name)
            response = json.loads(request('https://api.openai.com/v1/responses', payload=payload,
                headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}))
            # Save provider output before validation so a failed draft is not hidden or rerun.
            output.write_text(json.dumps({'model': model, 'input_sha256': digest, 'response': response}, indent=2))
            usage = response.get('usage') or {}
            with db: db.execute('UPDATE calls SET input_tokens=?,output_tokens=? WHERE id=?', (usage.get('input_tokens'), usage.get('output_tokens'), call_id))
            if response.get('status') != 'completed': raise ValueError(name + ': incomplete response saved; no automatic retry')
            parts = [c['text'] for item in response.get('output', []) for c in item.get('content', []) if c.get('type') == 'output_text']
            draft = json.loads(''.join(parts))
            validate_draft(draft, {'text': evidence_text(evidence)}); validate_podcast(draft, source)
            (ROOT / (name + '-draft.md')).write_text('# ' + draft['title'] + '\n\n' + draft['body'])
            print(name + ': draft saved; needs blinded editorial scoring')
    finally: db.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--live', action='store_true'); args = parser.parse_args()
    source, packet, result = audit()
    for name, r in result['versions'].items(): print(f"{name}: {r['retained']}/{r['total']} curated evidence checks; {r['core_retained']}/{r['core_total']} core; {r['characters']} chars")
    if args.live:
        try: paired_drafts(source, packet)
        except ValueError as e: parser.exit(1, str(e) + '\n')
