"""Local tokenizer measurements; install tiktoken to run. No model calls."""
import json
from pathlib import Path
import tiktoken

root = Path(__file__).resolve().parent / 'leaf'
try:
    encoding = tiktoken.encoding_for_model('gpt-5.6-luna')
    approximate = False
except KeyError:
    encoding = tiktoken.get_encoding('o200k_base')
    approximate = True
source = json.loads((root / 'source.json').read_text())
after = json.loads((root / 'after.json').read_text())
before = json.loads((root / 'before.json').read_text())

def plain(packet):
    # Include exactly the same metadata and evidence as JSON for a fair comparison.
    header = [f'{key}: {value}' for key, value in packet.items() if key != 'passages']
    return '\n'.join(header + [''] + [f"[{p['id']} | {p['section']}]\n{p['text']}\n" for p in packet['passages']])

full = {'source_title': source['title'], 'source_attribution': source['attribution'],
        'scope': 'Complete extracted main-article text; no figure pixels or supplementary files.',
        'passages': [{'id': 'full', 'section': 'Full main-article text', 'text': source['text']}]}
variants = {'full_json': json.dumps(full, ensure_ascii=False),
            'slim_v1_json': json.dumps(before, ensure_ascii=False),
            'slim_v2_json': json.dumps(after, ensure_ascii=False),
            'slim_v2_pretty_json': json.dumps(after, ensure_ascii=False, indent=2),
            'slim_v2_compact_json': json.dumps(after, ensure_ascii=False, separators=(',', ':')),
            'slim_v2_labelled_text': plain(after)}
result = {'encoding': encoding.name, 'fallback_encoding': approximate,
          'scope': 'Local source-input text counts only. Excludes instructions, schema and API framing. Fallback encoding is not verified for Luna; not billed usage.',
          'counts': {key: len(encoding.encode(value)) for key, value in variants.items()}}
(root / 'tokens.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
