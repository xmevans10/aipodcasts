"""Objective proxies for audition clips (not a substitute for listening): pace, pause share, pitch expressiveness."""
import array, json, math, re, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
SR = 16000

def pcm(path):
    # ffmpeg is optional; macOS afconvert is always present
    import tempfile, wave
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'clip.wav'
        subprocess.run(['afconvert', '-f', 'WAVE', '-d', f'LEI16@{SR}', '-c', '1', str(path), str(wav)], check=True)
        with wave.open(str(wav)) as w:
            return array.array('h', w.readframes(w.getnframes()))

def f0(frame):
    n = len(frame); energy = sum(x * x for x in frame)
    if energy < n * 400 ** 2: return None
    best, lag_best = 0, 0
    for lag in range(SR // 400, SR // 70):  # 70-400 Hz
        c = sum(frame[i] * frame[i + lag] for i in range(0, n - lag, 2))
        if c > best: best, lag_best = c, lag
    return SR / lag_best if lag_best and best > 0.3 * energy / 2 else None

def score(path, text):
    s = pcm(path); dur = len(s) / SR
    hop, win = 320, 640  # 20 ms hop
    rms = [math.sqrt(sum(x * x for x in s[i:i + hop]) / hop) for i in range(0, len(s) - hop, hop)]
    thresh = max(rms) * 0.05
    pause = sum(r < thresh for r in rms) / len(rms)
    pitches = [p for i in range(0, len(s) - win, hop * 2) if (p := f0(s[i:i + win]))]
    st = [12 * math.log2(p / 100) for p in pitches]
    mean = sum(st) / len(st); sd = math.sqrt(sum((x - mean) ** 2 for x in st) / len(st))
    words = len(re.sub(r'\[[^\]]*\]', '', text).split())
    return {'seconds': round(dur, 1), 'wpm': round(words / dur * 60), 'pause_share': round(pause, 2),
            'median_hz': round(sorted(pitches)[len(pitches) // 2]), 'pitch_sd_semitones': round(sd, 2)}

if __name__ == '__main__':
    from audition import LINES, CANDIDATES
    out = {}
    for host, voices in CANDIDATES.items():
        for name, vid in voices.items():
            clip = HERE / 'clips' / f'{host}--{vid}.mp3'
            if clip.exists():
                out.setdefault(host, {})[name] = {'voice_id': vid, **score(clip, LINES[host])}
                print(host, name, out[host][name], flush=True)
    (HERE / 'scores.json').write_text(json.dumps(out, indent=1))
