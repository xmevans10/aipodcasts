"""Bounded, explicit private-preview TTS. Never changes editorial publication records.

Run --check first; --generate HOST performs exactly one non-retried paid request.
An attempt is recorded before sending: ambiguous failures require manual reconciliation.
"""
from __future__ import annotations
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request
import urllib.error
from pipeline import load_local_env

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / 'demos/three-hosts-2026-09-17/manifest.json'


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def check(path):
    manifest = json.loads(path.read_text())
    if manifest['status'] != 'private_preview_not_published':
        raise ValueError('This tool only generates private review samples')
    if manifest['tts_model'] != 'eleven_multilingual_v2':
        raise ValueError('Unexpected model; review budget before changing it')
    if len(manifest['episodes']) != 3 or len({e['id'] for e in manifest['episodes']}) != 3:
        raise ValueError('Expected three distinct episodes')
    total = 0
    for e in manifest['episodes']:
        script_path = (path.parent / e['script_file']).resolve()
        if script_path.parent != path.parent.resolve():
            raise ValueError('Scripts must be beside manifest')
        script = script_path.read_text()
        if hashlib.sha256(script.encode()).hexdigest() != e['script_sha256']:
            raise ValueError('Script changed since source review: ' + e['id'])
        if not 350 <= len(script.split()) <= 500 or len(script) > 4000:
            raise ValueError('Episode exceeds preview length limits')
        if len(script) != e['character_count']:
            raise ValueError('Character estimate is stale')
        for source in e['sources']:
            if not source['url'].startswith('https://') or not source['authors']:
                raise ValueError('Missing secure source link or attribution')
        total += len(script)
    if total > manifest['max_total_characters'] or manifest['max_generation_attempts'] > 3:
        raise ValueError('Preview budget exceeded')
    return manifest, total


def generate(path, host, retry_rejected=False):
    load_local_env()
    key = os.environ.get('ELEVENLABS_API_KEY')
    if not key:
        raise ValueError('ELEVENLABS_API_KEY is not configured')
    ledger_path = path.parent / 'generation-ledger.json'
    lock = (path.parent / '.generation.lock').open('a')
    with lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        manifest, total = check(path)
        e = next(x for x in manifest['episodes'] if x['id'] == host)
        voice = e.get('voice') or {}
        if not re.fullmatch('[A-Za-z0-9_-]+', voice.get('voice_id', '')):
            raise ValueError('Select a verified voice ID first')
        audio = path.parent / (host + '.mp3')
        if audio.exists():
            print(json.dumps({'host': host, 'status': 'existing_audio_reused', 'file': str(audio)})); return
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {'attempts': []}
        def rejected(a):
            return a.get('status') == 'http_error' and a.get('http_status') in (401, 402)
        if sum(not rejected(a) for a in ledger['attempts']) >= manifest['max_generation_attempts']:
            raise ValueError('Three-attempt preview limit reached')
        prior = [a for a in ledger['attempts'] if a['host'] == host]
        if prior and not (retry_rejected and all(rejected(a) for a in prior)):
            raise ValueError('Prior attempt exists; only explicit retry of a rejected authentication/payment request is permitted')
        attempt = {'host': host, 'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                   'characters': e['character_count'], 'voice_id': voice['voice_id'],
                   'script_sha256': e['script_sha256'], 'model_id': manifest['tts_model'],
                   'status': 'reserved_before_request'}
        ledger['attempts'].append(attempt); save(ledger_path, ledger)
        script = (path.parent / e['script_file']).read_text()
        settings = voice.get('settings', {'stability': 0.55, 'similarity_boost': 0.75, 'style': 0, 'use_speaker_boost': True})
        payload = {'text': script, 'model_id': manifest['tts_model'], 'language_code': 'en', 'voice_settings': settings}
        save(path.parent / (host + '-request.json'), payload)
        req = urllib.request.Request('https://api.elevenlabs.io/v1/text-to-speech/' + voice['voice_id'] + '?output_format=mp3_44100_128',
            data=json.dumps(payload).encode(), headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs): return None
        try:
            with urllib.request.build_opener(NoRedirect).open(req, timeout=150) as response:
                data = response.read(15000001)
                headers = {k.lower(): v for k,v in response.headers.items() if k.lower() in {'request-id','x-request-id','history-item-id','character-cost','x-character-count','content-type'}}
            if len(data) > 15000000 or len(data) < 1000 or not (data[:3] == b'ID3' or (data[0] == 255 and data[1] & 224 == 224)):
                raise ValueError('Response is not a valid-sized MP3')
            temporary=audio.with_suffix('.mp3.tmp'); temporary.write_bytes(data); temporary.replace(audio)
            attempt.update(status='audio_received', bytes=len(data), response_metadata=headers)
            e.update(audio_file=audio.name, audio_status='generated_pending_listening_review')
            save(path, manifest)
            print(json.dumps({'host':host, 'status':'generated', 'bytes':len(data), 'characters':len(script), 'response_metadata':headers, 'file':str(audio)}))
        except urllib.error.HTTPError as error:
            attempt.update(status='http_error', http_status=error.code, error=error.read(1600).decode(errors='replace').replace(key,'[REDACTED]'))
            print(json.dumps({'host':host, 'status':'failed', 'http_status':error.code, 'error':attempt['error']}))
            raise SystemExit(1)
        except Exception as error:
            attempt.update(status='ambiguous_failure_do_not_retry', error=str(error).replace(key,'[REDACTED]'))
            raise
        finally:
            save(ledger_path, ledger)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, default=DEFAULT)
    a=p.add_mutually_exclusive_group(required=True)
    a.add_argument('--check', action='store_true'); a.add_argument('--generate', choices=['mira','clara','elias'])
    p.add_argument('--retry-rejected', action='store_true', help='Explicitly retry a prior 401/402 after access is fixed; never retries ambiguous requests')
    args=p.parse_args()
    if args.check:
        m,n=check(args.manifest);print(json.dumps({'episodes':len(m['episodes']),'characters':n,'limit':m['max_total_characters'],'max_paid_attempts':m['max_generation_attempts'],'voices_selected':sum(bool(e.get('voice')) for e in m['episodes'])}))
    else:generate(args.manifest,args.generate,args.retry_rejected)
