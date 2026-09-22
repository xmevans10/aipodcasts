#!/usr/bin/env python3
"""Render the weekly transcripts to audio with Kokoro and bundle them for the app.

Solo shows only, for now. Each host keeps its distinct Kokoro-82M fixed voicepack from
tools/tts/voice_cast.json (Apache-2.0 code and weights; no cloning, no key, no consent).
Co-hosted shows (Ground Truth, Star Bros) are deferred until multi-speaker narration is
settled, so they are skipped rather than half-rendered.

For each show it writes ios/Zwicky/Episodes/<slug>.m4a plus <slug>.json in the shape the
app's BundledEpisode decoder expects (story, duration, word-timed transcript, envelope),
and refreshes Episodes/index.json. Word timings are distributed by word length across the
real audio duration, since Kokoro reads the exact reviewed script.

    python3 tools/tts/bundle_shows.py --transcripts experiments/full-run/<run>/transcripts
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from envelope import HOP, envelope_wav  # noqa: E402
from hosts import HOSTS, dialogue_hosts  # noqa: E402

SR = 24000


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def load_cast(path: Path) -> dict:
    data = json.loads(path.read_text())
    return {k: v for k, v in data.items() if not k.startswith("_")}


def episode_key(published: str, doi: str, show: str) -> str:
    """Opaque, deterministic per-episode identifier; the audio key and feed use it.

    Deterministic so re-rendering the same episode keeps its id (saved/queue history
    survives), opaque so audio cannot be guessed from the show name.
    """
    return hashlib.sha256(f"{slug(show)}|{published}|{doi}".encode()).hexdigest()[:16]


def timings(words: list[str], duration: float) -> list[float]:
    """Monotonic start time per word, spread by word length across the audio."""
    weights = [len(w) + 1 for w in words]
    total = sum(weights) or 1
    starts, cumulative = [], 0.0
    for weight in weights:
        starts.append(round(min(duration, duration * cumulative / total), 3))
        cumulative += weight
    return starts


def https(url: str, doi: str = "") -> str:
    if url.startswith("https://"):
        return url
    if url.startswith("http://"):
        return "https://" + url[len("http://"):]
    if doi:
        return "https://doi.org/" + doi
    return url


def story_for(transcript: dict, duration: float, published: str, episode: str = None) -> dict:
    """Build the app Story + transcript payload from one full-run transcript artifact."""
    draft, source = transcript["draft"], transcript["source"]
    host = transcript["host"]
    name = episode or slug(transcript["show"])
    body = draft["body"].strip()
    words = body.split()
    starts = timings(words, duration)
    meta = HOSTS.get(host)
    topic = (meta.topic.upper() if meta and meta.topic else transcript["show"].upper())
    return {
        "story": {
            "id": "episode-" + name,
            "title": draft["title"],
            "dek": draft["dek"],
            "topic": topic,
            "hostID": host,
            "minutes": max(1, round(duration / 60)),
            "body": body,
            "caveat": draft["caveat"],
            "sources": [{
                "title": source.get("title") or "Source paper",
                "url": https(source.get("url", ""), source.get("doi", transcript.get("doi", ""))),
                "attribution": source.get("attribution") or "Authors listed at source",
                "license": source.get("license") or "See source",
            }],
            "audioURL": "bundle:" + name + ".m4a",
            "isDemo": False,
            "published": published,
        },
        "duration": round(duration, 2),
        "transcript": [{"words": [{"text": w, "start": s} for w, s in zip(words, starts)]}],
        "levelHop": HOP,
    }


def to_m4a(wav: Path, dest: Path) -> None:
    if shutil.which("afconvert"):
        try:
            subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", str(wav), str(dest)],
                           check=True, capture_output=True)
            return
        except subprocess.CalledProcessError:
            pass  # some WAV rate/channel combos are rejected; fall back to ffmpeg
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                        "-c:a", "aac", "-b:a", "96k", str(dest)], check=True)
        return
    raise SystemExit("Need afconvert (macOS) or ffmpeg to encode m4a")


def wav_duration(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


_PIPELINES: dict = {}


def render_kokoro(text: str, voice: str, speed: float):
    """Render text in one Kokoro voice; pipelines are cached per language (model load is slow)."""
    import numpy as np
    from kokoro import KPipeline

    language = "b" if voice.startswith("b") else "a"
    if language not in _PIPELINES:
        _PIPELINES[language] = KPipeline(lang_code=language)
    chunks = [audio for _, _, audio in _PIPELINES[language](text, voice=voice, speed=speed)]
    return np.concatenate(chunks) if chunks else np.zeros(SR, dtype="float32")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcripts", required=True, help="a full-run transcripts directory")
    parser.add_argument("--out", default=str(ROOT / "ios/Zwicky/Episodes"))
    parser.add_argument("--voices", default=str(ROOT / "tools/tts/voice_cast.json"))
    parser.add_argument("--date", default="")
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args()

    import datetime as dt
    published = args.date or dt.date.today().isoformat()
    cast = load_cast(Path(args.voices))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    legacy = sorted(p.stem for p in out.glob("*.json") if p.stem != "index")

    rendered, skipped = [], []
    for path in sorted(Path(args.transcripts).glob("*.json")):
        transcript = json.loads(path.read_text())
        host = transcript.get("host", "")
        if dialogue_hosts(host):
            skipped.append(f"{transcript['show']} (co-hosted: deferred)")
            continue
        voice = (cast.get(host) or {}).get("voice")
        if not voice:
            skipped.append(f"{transcript['show']} (no cast voice for {host})")
            continue
        name = episode_key(published, transcript.get("doi", ""), transcript["show"])
        wav = out / f"{name}.wav"
        print(f"rendering {transcript['show']} -> {name} voice={voice} ...", flush=True)
        import soundfile as sf
        audio = render_kokoro(transcript["draft"]["body"].strip(), voice, args.speed)
        sf.write(str(wav), audio, SR)
        duration = wav_duration(wav)
        payload = story_for(transcript, duration, published, episode=name)
        payload["levels"] = envelope_wav(wav)
        to_m4a(wav, out / f"{name}.m4a")
        wav.unlink()
        (out / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False) + "\n")
        print(f"  {duration:.1f}s, {len(payload['levels'])} level frames", flush=True)
        rendered.append(name)

    index = sorted(set(legacy) | set(rendered))
    (out / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(f"bundled {len(rendered)} episode(s); index has {len(index)}")
    for note in skipped:
        print("  skipped:", note)


if __name__ == "__main__":
    main()
