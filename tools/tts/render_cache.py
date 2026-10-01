"""Reuse only completed, byte-verified renders with identical production inputs."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(transcript: dict, cast: dict, provider: str, speed: float, day: str) -> str:
    dependencies = ['tools/tts/bundle_shows.py', 'tools/tts/cloud_tts.py',
                    'tools/tts/sound_design.py', 'tools/tts/mastering.py',
                    'tools/tts/align.py', 'backend/envelope.py', 'backend/hosts.py']
    inputs = {'transcript': transcript, 'cast': cast, 'provider': provider,
              'speed': speed, 'day': day,
              'code': {name: sha256(ROOT / name) for name in dependencies}}
    # Also bind packaged cue assets; changing a waveform must invalidate reuse.
    assets = ROOT / 'assets/audio/kenney'
    inputs['assets'] = {str(p.relative_to(ROOT)): sha256(p)
                        for p in sorted(assets.rglob('*')) if p.is_file()}
    return hashlib.sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def reusable(directory: Path, name: str, expected: str) -> bool:
    metadata, audio = directory / f'{name}.json', directory / f'{name}.m4a'
    if not metadata.is_file() or not audio.is_file():
        return False
    try:
        payload = json.loads(metadata.read_text())
        provenance = payload.get('renderProvenance') or {}
        if (provenance.get('inputSHA256') != expected
                or provenance.get('audioSHA256') != sha256(audio)):
            return False
        # Check identity, complete script/timing and container before another reuse.
        import sys
        sys.path.insert(0, str(ROOT / 'tools'))
        from publish_feed import validate_rendered_episodes
        validate_rendered_episodes([{**payload, '_file': str(metadata)}], directory)
        from mastering import validate_encoded
        validate_encoded(audio)
        return True
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError):
        return False


def save_json(path: Path, value) -> None:
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')
    temporary.replace(path)
