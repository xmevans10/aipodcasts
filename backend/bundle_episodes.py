"""Package produced preview episodes for the iOS app: audio + story metadata + word-timed transcript.

Word timings come from ElevenLabs Scribe on the final mix, aligned onto the canonical script text
(so the app shows the reviewed script, not the ASR transcript). Cached per audio hash.

python3 backend/bundle_episodes.py
"""
from __future__ import annotations
import difflib, hashlib, json, os, re, shutil, sys, urllib.request, uuid
from pathlib import Path
from envelope import envelope, HOP
from pipeline import load_local_env

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / 'demos/three-hosts-2026-09-17'
OUT = ROOT / 'ios/Zwicky/Episodes'


def norm(token):
    return re.sub(r"[^a-z0-9' ]", ' ', token.lower().replace('-', ' ').replace('’', "'")).split()


def scribe_words(key, audio):
    cache = DEMO / 'beats' / f"scribe-{hashlib.sha256(audio.read_bytes()).hexdigest()[:16]}.json"
    if cache.exists(): return json.loads(cache.read_text())
    b = uuid.uuid4().hex
    fields = {'model_id': 'scribe_v1', 'language_code': 'en', 'timestamps_granularity': 'word', 'tag_audio_events': 'false'}
    body = b''.join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items())
    body += f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{audio.name}"\r\nContent-Type: audio/mp4\r\n\r\n'.encode() + audio.read_bytes() + f'\r\n--{b}--\r\n'.encode()
    req = urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text', data=body, headers={'xi-api-key': key, 'Content-Type': 'multipart/form-data; boundary=' + b})
    with urllib.request.urlopen(req, timeout=300) as r:
        words = [{'text': w['text'], 'start': w['start'], 'end': w['end']} for w in json.load(r)['words'] if w.get('type') == 'word']
    cache.write_text(json.dumps(words)); return words


def align(paragraphs, heard):
    """Give every script token a start time by aligning normalized script words to timed ASR words."""
    tokens = [(p, t) for p, text in enumerate(paragraphs) for t in text.split()]
    flat, owner = [], []  # normalized script words and the token each belongs to
    for i, (_, tok) in enumerate(tokens):
        for w in norm(tok) or ['']: flat.append(w); owner.append(i)
    hflat, htime = [], []
    for w in heard:
        parts = norm(w['text']) or ['']
        span = (w['end'] - w['start']) / len(parts)
        for j, part in enumerate(parts): hflat.append(part); htime.append((w['start'] + j * span, w['start'] + (j + 1) * span))
    times = [None] * len(flat)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, flat, hflat, autojunk=False).get_opcodes():
        if tag == 'equal' or (tag == 'replace' and i2 - i1 == j2 - j1):
            for k in range(i2 - i1): times[i1 + k] = htime[j1 + k]
        elif tag == 'replace':  # spread the heard span across the script words (e.g. digits vs spelled numbers)
            start, end = htime[j1][0], htime[j2 - 1][1]
            for k in range(i2 - i1):
                times[i1 + k] = (start + (end - start) * k / (i2 - i1), start + (end - start) * (k + 1) / (i2 - i1))
    # interpolate anything unmatched between known neighbours
    known = [i for i, t in enumerate(times) if t]
    for i in range(len(times)):
        if times[i]: continue
        prev = max((k for k in known if k < i), default=None); nxt = min((k for k in known if k > i), default=None)
        a = times[prev][1] if prev is not None else 0.0
        b = times[nxt][0] if nxt is not None else a + 0.3
        times[i] = (a, max(a, b))
    token_start = {}
    for idx, i in enumerate(owner): token_start.setdefault(i, times[idx][0])
    out = [{'words': []} for _ in paragraphs]
    for i, (p, tok) in enumerate(tokens):
        out[p]['words'].append({'text': tok, 'start': round(token_start[i], 2)})
    # enforce monotonic timings so highlighting never jumps backwards
    last = 0.0
    for para in out:
        for w in para['words']:
            w['start'] = last = max(last, w['start'])
    return out


def main():
    load_local_env(); key = os.environ['ELEVENLABS_API_KEY']
    plan = {e['id']: e for e in json.loads((DEMO / 'production.json').read_text())['episodes']}
    manifest = json.loads((DEMO / 'manifest.json').read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    for m in manifest['episodes']:
        p = plan[m['id']]; audio = DEMO / p['audio_file']
        paragraphs = [para.strip() for b in p['beats'] for para in b['text'].split('\n\n') if para.strip()]
        transcript = align(paragraphs, scribe_words(key, audio))
        story = {
            'id': 'episode-' + m['id'], 'title': m['title'], 'dek': m['dek'], 'topic': m['niche'].upper(),
            'hostID': m['host_id'], 'minutes': max(1, round(p['duration_seconds'] / 60)),
            'body': '\n\n'.join(paragraphs),
            'caveat': m.get('caveat', 'AI-assisted preview episode. Sources checked by the assistant; independent editorial approval is still pending. Host and narration are AI-generated.'),
            'sources': [{'title': s['title'], 'url': s['url'], 'attribution': ', '.join(s['authors']), 'license': s['license']} for s in m['sources']],
            'audioURL': 'bundle:' + m['id'] + '.m4a', 'isDemo': False, 'published': manifest['created'],
        }
        shutil.copyfile(audio, OUT / f"{m['id']}.m4a")
        levels = envelope(audio)  # five-band levels for the animated cover
        (OUT / f"{m['id']}.json").write_text(json.dumps(
            {'story': story, 'duration': p['duration_seconds'], 'transcript': transcript,
             'levelHop': HOP, 'levels': levels}, ensure_ascii=False) + '\n')
        n = sum(len(x['words']) for x in transcript)
        print(m['id'], 'paragraphs', len(transcript), 'words', n, 'level frames', len(levels), 'of', p['duration_seconds'], 's')


if __name__ == '__main__':
    main()
