"""Render six private character calibration takes; never publish them as episodes."""
import argparse
import json
import sys
import wave
from pathlib import Path
from unittest.mock import patch

import numpy as np

root = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(root / 'tools/tts'), str(root / 'backend')]
import cloud_tts
from bundle_shows import to_m4a

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, default=root / 'build/host-personality-preview')
out = parser.parse_args().out
out.mkdir(parents=True, exist_ok=True)
cast = json.loads((root / 'tools/tts/voice_cast.json').read_text())
scripts = {
    'atlas': "I'd like to give you a simple answer. We haven't got one yet. That can be frustrating. But we do have something to go on, and I'd rather walk through that with you than pretend the story is finished.",
    'fern': "Oh, I like this bird already. There's a lovely little puzzle here, and I want to know more. All right, I'm getting ahead of myself. Let's follow what it actually did, and see how much we can honestly explain.",
    'noor': "Very confident answer. Slight problem: confidence wasn't what we were testing. I know, I wanted this to be clever too. It might be. Let's give it a fair test before we start printing the victory shirts.",
}
results = []
for host, text in scripts.items():
    voice = cast[host]
    for mode in ('baseline', 'directed'):
        dest = out / f'{host}-{mode}.m4a'
        if dest.exists():
            print(f'already rendered: {dest.name}', flush=True)
            continue
        if mode == 'baseline':
            with patch.object(cloud_tts, 'narration_direction', return_value='Use clear, natural conversational delivery.'):
                audio = cloud_tts.synthesize(text, voice['geminiVoice'], voice['accent'], host_id=host, passage='complete')
        else:
            audio = cloud_tts.synthesize(text, voice['geminiVoice'], voice['accent'], host_id=host, passage='complete')
        if not len(audio) or not np.isfinite(audio).all() or np.max(np.abs(audio)) < 0.01:
            raise ValueError('Empty, invalid or silent preview')
        wav = dest.with_suffix('.wav')
        with wave.open(str(wav), 'wb') as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(cloud_tts.SAMPLE_RATE)
            stream.writeframes((np.clip(audio, -1, 1) * 32767).astype('<i2').tobytes())
        to_m4a(wav, dest)
        duration = len(audio) / cloud_tts.SAMPLE_RATE
        results.append({'host': host, 'mode': mode, 'seconds': round(duration, 2), 'path': str(dest)})
        print(f'{host} {mode}: {duration:.1f}s', flush=True)
(out / 'preview-results.json').write_text(json.dumps(results, indent=2) + '\n')
