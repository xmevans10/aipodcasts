"""Five-band audio envelope for the animated cover.

Goertzel energy at five centre frequencies, every 100 ms, normalised per episode.
Pure Python on top of macOS `afconvert`; no numpy, no ffmpeg. The app feeds these
levels into the Rive cover so the bars follow the actual narration.
"""
from __future__ import annotations
import array, math, subprocess, tempfile, wave
from pathlib import Path

SR = 16000
HOP = 0.1                      # seconds per frame
BANDS = (140, 380, 900, 2100, 4200)


def decode(path: Path) -> array.array:
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'a.wav'
        subprocess.run(['afconvert', '-f', 'WAVE', '-d', f'LEI16@{SR}', '-c', '1', str(path), str(wav)], check=True)
        with wave.open(str(wav)) as w:
            return array.array('h', w.readframes(w.getnframes()))


def goertzel(samples, start, length, frequency):
    """Energy at one frequency over one window (Goertzel, one bin, no FFT needed)."""
    k = 2 * math.cos(2 * math.pi * frequency / SR)
    s1 = s2 = 0.0
    for i in range(start, min(start + length, len(samples))):
        s0 = samples[i] / 32768 + k * s1 - s2
        s2, s1 = s1, s0
    return math.sqrt(max(0.0, s1 * s1 + s2 * s2 - k * s1 * s2)) / max(1, length)


def envelope(path: Path, hop: float = HOP) -> list[list[float]]:
    """Per-frame levels for each band, 0..1, normalised against the episode's own 95th percentile."""
    samples = decode(path)
    window = int(hop * SR)
    frames = []
    for start in range(0, len(samples) - 1, window):
        frames.append([goertzel(samples, start, window, f) for f in BANDS])
    for band in range(len(BANDS)):
        values = sorted(frame[band] for frame in frames)
        ceiling = values[int(len(values) * 0.95)] if values else 0
        if ceiling <= 0:
            continue
        for frame in frames:
            frame[band] = round(min(1.0, frame[band] / ceiling), 3)
    return frames


if __name__ == '__main__':
    import json, sys
    for name in sys.argv[1:]:
        frames = envelope(Path(name))
        print(json.dumps({'file': name, 'frames': len(frames), 'first': frames[:3], 'peak': max(max(f) for f in frames)}))
