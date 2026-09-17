"""Transcribe produced episodes and diff against their scripts (catches dropped, invented or garbled lines)."""
import difflib, json, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / 'voices'), str(HERE.parent)]
from transcribe import transcribe, words
from pipeline import load_local_env

D = HERE.parents[1] / 'demos/three-hosts-2026-09-17'
if __name__ == '__main__':
    load_local_env(); key = os.environ['ELEVENLABS_API_KEY']
    plan = json.loads((D / 'production.json').read_text())
    path = D / 'qa-transcripts.json'; report = json.loads(path.read_text()) if path.exists() else {}
    for e in plan['episodes']:
        if sys.argv[1:] and e['id'] not in sys.argv[1:]: continue
        heard = transcribe(key, D / e['audio_file']); exp = words(' '.join(b['text'] for b in e['beats'])); got = words(heard)
        sm = difflib.SequenceMatcher(None, exp, got, autojunk=False)
        diffs = [(t, ' '.join(exp[i1:i2]), ' '.join(got[j1:j2])) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != 'equal']
        report[e['id']] = {'voice': e['voice_name'], 'match': round(sm.ratio(), 3), 'wpm': round(len(got) / e['duration_seconds'] * 60), 'seconds': e['duration_seconds'], 'diffs': diffs, 'transcript': heard}
        print(e['id'], report[e['id']]['match'], 'wpm', report[e['id']]['wpm'], diffs)
    path.write_text(json.dumps(report, indent=1))
