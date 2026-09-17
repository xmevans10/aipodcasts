"""Transcribe audition clips with ElevenLabs Scribe to catch mispronunciations and spoken audio tags."""
import difflib, json, os, re, sys, urllib.request, uuid
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from pipeline import load_local_env
from audition import LINES, CANDIDATES

def words(t): return re.sub(r"[^a-z' ]", ' ', re.sub(r'\[[^\]]*\]|\([^)]*\)', ' ', t.lower()).replace('-', ' ')).split()

def transcribe(key, clip):
    b = uuid.uuid4().hex
    fields = {'model_id': 'scribe_v1', 'tag_audio_events': 'true', 'language_code': 'en'}
    body = b''.join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items())
    body += f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="clip.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode() + clip.read_bytes() + f'\r\n--{b}--\r\n'.encode()
    req = urllib.request.Request('https://api.elevenlabs.io/v1/speech-to-text', data=body, headers={'xi-api-key': key, 'Content-Type': 'multipart/form-data; boundary=' + b})
    with urllib.request.urlopen(req, timeout=120) as r: return json.load(r)['text']

if __name__ == '__main__':
    load_local_env(); key = os.environ['ELEVENLABS_API_KEY']
    scores = json.loads((HERE / 'scores.json').read_text())
    for host, voices in CANDIDATES.items():
        for name, vid in voices.items():
            clip = HERE / 'clips' / f'{host}--{vid}.mp3'
            row = scores[host][name]
            if 'transcript' in row or not clip.exists(): continue
            text = transcribe(key, clip)
            expected, heard = words(LINES[host]), words(text)
            row.update(transcript=text, word_match=round(difflib.SequenceMatcher(None, expected, heard).ratio(), 3),
                       spoken_tags=[t for t in ('curious', 'thoughtful', 'excited', 'pause', 'laughs', 'softly') if t in heard and t not in expected])
            print(host, name, row['word_match'], row['spoken_tags'], text[:110], flush=True)
    (HERE / 'scores.json').write_text(json.dumps(scores, indent=1))
