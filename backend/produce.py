"""Directed multi-beat episode production for private previews (Eleven v3 + local mix).

Each beat is synthesized separately and cached by content hash (voice, model, settings, text),
so re-running never re-buys unchanged lines and one bad take costs only its beat.
Mixing is local: intro jingle, shared transition sting, pauses, loudness levelling, AAC encode.

python3 backend/produce.py [HOST ...] [--dry-run] [--max-chars 10000]
"""
from __future__ import annotations
import argparse, array, hashlib, json, math, os, subprocess, tempfile, time, urllib.error, urllib.request, wave
from pathlib import Path
from pipeline import load_local_env

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / 'demos/three-hosts-2026-09-17'
CACHE = DEMO / 'beats'
SR = 44100
TARGET_RMS_DBFS = -20.0  # speech RMS; lands near -16 LUFS for dialogue


def beat_key(voice_id, model, settings, text):
    return hashlib.sha256(json.dumps([voice_id, model, settings, text], sort_keys=True).encode()).hexdigest()[:20]


def synthesize(key, voice_id, model, settings, text, out):
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128',
        data=json.dumps({'text': text, 'model_id': model, 'language_code': 'en', 'voice_settings': settings}).encode(),
        headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    if len(data) < 1000 or not (data[:3] == b'ID3' or (data[0] == 255 and data[1] & 224 == 224)):
        raise ValueError('response is not an MP3')
    tmp = out.with_suffix('.tmp'); tmp.write_bytes(data); tmp.replace(out)


def decode(path) -> array.array:
    """Any audio file -> mono float samples at SR (via macOS afconvert)."""
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'x.wav'
        subprocess.run(['afconvert', '-f', 'WAVE', '-d', f'LEI16@{SR}', '-c', '1', str(path), str(wav)], check=True)
        with wave.open(str(wav)) as w:
            pcm = array.array('h', w.readframes(w.getnframes()))
    return array.array('f', (x / 32768 for x in pcm))


def rms_db(s):
    voiced = [x for x in s if abs(x) > 0.01] or [1e-6]
    return 20 * math.log10(math.sqrt(sum(x * x for x in voiced) / len(voiced)))


def gain(s, db):
    g = 10 ** (db / 20)
    return array.array('f', (x * g for x in s))


def fade(s, fade_in=0.0, fade_out=0.0):
    s = array.array('f', s); n_in, n_out = int(fade_in * SR), int(fade_out * SR)
    for i in range(min(n_in, len(s))): s[i] *= i / n_in
    for i in range(min(n_out, len(s))): s[-1 - i] *= i / n_out
    return s


def trim_silence(s, threshold=0.004, keep=0.08):
    idx = [i for i, x in enumerate(s) if abs(x) > threshold]
    if not idx: return s
    pad = int(keep * SR)
    return s[max(0, idx[0] - pad):min(len(s), idx[-1] + pad)]


def silence(seconds): return array.array('f', bytes(4 * int(seconds * SR)))


def mix_episode(episode, beat_files, transition, gap, transition_db):
    out = array.array('f')
    if episode.get('intro_asset'):
        intro = decode((DEMO / episode['intro_asset']).resolve())
        out += fade(gain(intro, TARGET_RMS_DBFS - 4 - rms_db(intro)), 0.02, 1.5)
        out += silence(0.35)
    for i, (beat, path) in enumerate(zip(episode['beats'], beat_files)):
        voice = trim_silence(decode(path))
        out += gain(voice, TARGET_RMS_DBFS - rms_db(voice))
        if i < len(episode['beats']) - 1:
            out += silence(beat.get('pause_after_seconds', gap))
            if beat.get('effect_after') == 'transition' and transition is not None:
                out += gain(transition, TARGET_RMS_DBFS + transition_db + 12 - rms_db(transition)) + silence(0.25)
    peak = max(abs(x) for x in out)
    if peak > 0.84: out = gain(out, 20 * math.log10(0.84 / peak))  # ~-1.5 dBTP ceiling
    return out


def write_m4a(samples, dest):
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'mix.wav'
        with wave.open(str(wav), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes(array.array('h', (max(-32767, min(32767, int(x * 32767))) for x in samples)).tobytes())
        subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '128000', str(wav), str(dest)], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('hosts', nargs='*'); ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--max-chars', type=int, default=10000)
    a = ap.parse_args()
    plan = json.loads((DEMO / 'production.json').read_text())
    model, settings, mix = plan['model_id'], plan['voice_settings'], plan['mix']
    CACHE.mkdir(exist_ok=True)
    ledger_path = CACHE / 'ledger.json'
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
    episodes = [e for e in plan['episodes'] if not a.hosts or e['id'] in a.hosts]
    todo = [(e, b) for e in episodes for b in e['beats']
            if not (CACHE / f"{e['id']}-{b['id']}-{beat_key(e['voice_id'], model, settings, b['directed_text'])}.mp3").exists()]
    cost = sum(len(b['directed_text']) for _, b in todo)
    print(json.dumps({'beats_to_generate': len(todo), 'characters': cost, 'cached_beats': sum(len(e['beats']) for e in episodes) - len(todo)}))
    if cost > a.max_chars: raise SystemExit(f'budget {a.max_chars} would be exceeded')
    if a.dry_run: return
    if todo:
        load_local_env(); key = os.environ['ELEVENLABS_API_KEY']
        for e, b in todo:
            path = CACHE / f"{e['id']}-{b['id']}-{beat_key(e['voice_id'], model, settings, b['directed_text'])}.mp3"
            entry = {'host': e['id'], 'beat': b['id'], 'voice_id': e['voice_id'], 'model': model, 'characters': len(b['directed_text']), 'utc': time.time()}
            try:
                synthesize(key, e['voice_id'], model, settings, b['directed_text'], path); entry['status'] = 'ok'
            except urllib.error.HTTPError as err:
                entry.update(status='http_error', http=err.code, error=err.read(300).decode(errors='replace').replace(key, '[K]'))
            ledger.append(entry); ledger_path.write_text(json.dumps(ledger, indent=1))
            print(e['id'], b['id'], entry['status'], entry.get('error', '')[:160], flush=True)
            if entry['status'] != 'ok': raise SystemExit(1)
    sting = ROOT / 'assets/audio/transition.mp3'
    transition = fade(decode(sting), 0.01, 0.4) if sting.exists() else None
    for e in episodes:
        files = [CACHE / f"{e['id']}-{b['id']}-{beat_key(e['voice_id'], model, settings, b['directed_text'])}.mp3" for b in e['beats']]
        samples = mix_episode(e, files, transition, mix['gap_seconds'], mix['transition_gain_db'])
        dest = DEMO / f"{e['id']}.m4a"; write_m4a(samples, dest)
        e['audio_file'] = dest.name; e['duration_seconds'] = round(len(samples) / SR, 1)
        print(json.dumps({'host': e['id'], 'file': str(dest.relative_to(ROOT)), 'seconds': e['duration_seconds']}))
    (DEMO / 'production.json').write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
