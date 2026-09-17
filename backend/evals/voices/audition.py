"""Bounded ElevenLabs voice audition: one short identical line per host across candidate voices.

Usage: python3 backend/evals/voices/audition.py [--only HOST] [--max-chars N]
Skips clips that already exist; records every attempt in ledger.json. Never prints the API key.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pipeline import load_local_env

HERE = Path(__file__).resolve().parent
OUT = HERE / 'clips'
MODEL = 'eleven_v3'
LINES = {
    'mira': "[curious] The Moon looks reassuringly finished. Craters in place. Dust settled. [short pause] But while we were getting on with life... something punched a brand-new hole in it.",
    'clara': "[curious] A dolphin chases a fish. So far, an entirely ordinary afternoon. [laughs softly] Then the fish brings up its last meal, and the dolphin eats that instead.",
    'elias': "[thoughtful] Your ordinary breath is, for a mosquito, a rather specialised signal. [excited] So how does a brain the size of a poppy seed actually pay attention?",
    'theo': "[grounded] The ocean takes its time. [warmly] A summer of heat can sit in the water for decades... and still be there when we have forgotten the summer.",
}
CANDIDATES = {
    'mira': {'Florence': '22N9cF8z0o7y23njdyaY', 'Amelia': 'ZF6FPAbjXT4488VcRRnw', 'Shelley': '4CrZuIW9am7gYAxgo2Af',
             'British (featured)': 'G17SuINrv2H9FC6nvetn', 'Alice': 'Xb7hH8MSUJpSbSDYk0k2', 'Lily': 'pFZP5JQG7iQjIQuC4Bku'},
    'clara': {'Maisie': 'QtY3JBOUKEB5xzrRfOKc', 'Australian (featured)': 'tyepWYJJwJM9TTFIg5U7', 'Hope': 'zGjIP4SZlMnY9m93k97r',
              'Juniper': 'aMSt68OGf4xUZAnLpTU8', 'Jessica Anne Bogart': 'g6xIsTj2HwM6VR4iXFCw', 'Cassidy': '56AoDkrOh6qfVPDXZ7Pt'},
    'elias': {'Lawrence': 'ktkP7Nsj67dw2zcplQYt', 'Archer': 'Fahco4VZzobUeiPqni1S', 'Chris': 'iP95p4xoKVk53GoZ742B',
              'Eric': 'cjVigY5qzO86Huf0OWal', 'Otto': 'FTNCalFNG5bRnkkaP5Ug', 'Peter': 'TumdjBNWanlT3ysvclWh', 'Liam': 'TX3LPaxmHKxFdv7VOQHJ'},
    'theo': {'Adam Stone': 'NFG5qt843uXKj4pFvR7C', 'John Doe': 'EiNlNiXeDU1pqqOPrYMO', 'Robert': 'BtWabtumIemAotTjP5sk',
             'Nassim': 'repzAAjoKlgcT2oOAIWt', 'Eric': 'cjVigY5qzO86Huf0OWal', 'Peter': 'TumdjBNWanlT3ysvclWh',
             'Archer': 'Fahco4VZzobUeiPqni1S', 'Brian': 'nPczCjzI2devNBz1zQrb', 'Bill': 'pqHfZKP75CvOlQylNhV4'},
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--only'); ap.add_argument('--limit', type=int, default=99)
    ap.add_argument('--max-chars', type=int, default=3500)
    a = ap.parse_args()
    load_local_env(); key = os.environ['ELEVENLABS_API_KEY']
    OUT.mkdir(exist_ok=True)
    ledger_path = HERE / 'ledger.json'
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
    spent = sum(x['characters'] for x in ledger if x['status'] != 'rejected')
    done = 0
    for host, voices in CANDIDATES.items():
        if a.only and host != a.only: continue
        for name, vid in voices.items():
            clip = OUT / f'{host}--{vid}.mp3'
            if clip.exists() or done >= a.limit: continue
            text = LINES[host]
            if spent + len(text) > a.max_chars: print('budget reached'); return
            entry = {'host': host, 'voice': name, 'voice_id': vid, 'model': MODEL, 'characters': len(text), 'utc': time.time(), 'status': 'reserved'}
            ledger.append(entry); ledger_path.write_text(json.dumps(ledger, indent=1))
            req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128',
                data=json.dumps({'text': text, 'model_id': MODEL, 'voice_settings': {'stability': 0.5}}).encode(),
                headers={'xi-api-key': key, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    data = r.read()
                clip.write_bytes(data); entry.update(status='ok', bytes=len(data)); spent += len(text)
            except urllib.error.HTTPError as e:
                body = e.read(400).decode(errors='replace').replace(key, '[K]')
                entry.update(status='rejected' if e.code in (400, 401, 402, 403, 404, 422) else 'error', http=e.code, error=body)
            done += 1
            ledger_path.write_text(json.dumps(ledger, indent=1))
            print(host, name, entry['status'], entry.get('http', ''), entry.get('error', '')[:200])
    print('characters spent (ok/error):', spent)


if __name__ == '__main__':
    main()
