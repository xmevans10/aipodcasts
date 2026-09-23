#!/usr/bin/env python3
"""Render the weekly transcripts to audio with Kokoro and bundle them for the app.

Solo and co-hosted shows use stable per-presenter Kokoro voicepacks (Apache-2.0).
Dialogue is rendered turn by turn; each turn's words are aligned to its own audio by
`align.py`, which reads the waveform (energy, silences, clause pauses) and fits the known
words with a phoneme-weighted duration model. Kokoro's own per-segment audio boundaries
anchor the alignment so a long turn cannot drift. No speaker labels are spoken aloud.

For each show it writes <episode-id>.m4a plus <episode-id>.json in the output directory in the shape the
app's BundledEpisode decoder expects (story, duration, word-timed transcript, envelope),
and refreshes Episodes/index.json.

    python3 tools/tts/bundle_shows.py --transcripts experiments/full-run/<run>/transcripts
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
import align  # noqa: E402
from envelope import HOP, envelope_wav  # noqa: E402
from podcast import validate_podcast
from verify import draft_fingerprint
import audience
from dialogue import turns_body, turns_narration_inputs, validate_dialogue_contract
from hosts import HOSTS, dialogue_hosts  # noqa: E402
from sound_design import SoundDesign  # noqa: E402

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


def story_for(transcript: dict, duration: float, published: str, episode: str = None, paragraphs: list | None = None) -> dict:
    """Build the app Story + transcript payload from one full-run transcript artifact."""
    draft, source = transcript["draft"], transcript["source"]
    host = transcript["host"]
    name = episode or slug(transcript["show"])
    body = turns_body(draft) if "turns" in draft else draft["body"].strip()
    words = body.split()
    starts = timings(words, duration)
    ends = starts[1:] + [round(duration, 3)] if starts else []
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
            **({"turns": draft["turns"], "hostIDs": [h.id for h in dialogue_hosts(host)]}
               if "turns" in draft else {}),
        },
        "duration": round(duration, 2),
        "transcript": paragraphs if paragraphs is not None else [
            {"words": [{"text": w, "start": s, "end": e} for w, s, e in zip(words, starts, ends)]}],
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
    """Render text in one Kokoro voice; pipelines are cached per language (model load is slow).

    Returns ``(audio, segments)``. Each segment is one Kokoro synthesis chunk with its
    text and sample count; those exact boundaries anchor the read-along alignment.
    """
    import numpy as np
    from kokoro import KPipeline

    language = "b" if voice.startswith("b") else "a"
    if language not in _PIPELINES:
        _PIPELINES[language] = KPipeline(lang_code=language)
    chunks, segments = [], []
    for result in _PIPELINES[language](text, voice=voice, speed=speed):
        graphemes = getattr(result, "graphemes", None)
        audio = getattr(result, "audio", None)
        if audio is None:  # older fastlane/kokoro builds yield a (graphemes, phonemes, audio) tuple
            graphemes, audio = result[0], result[2]
        if len(audio) == 0:
            continue
        chunks.append(audio)
        segments.append({"text": graphemes or "", "samples": len(audio)})
    if not chunks:
        raise ValueError("Kokoro returned no audio")
    return np.concatenate(chunks), segments


def render_google_cloud(text: str, voice: str, speed: float):
    if speed != 1.0:
        raise ValueError("Google Cloud Gemini TTS speed is instruction-controlled; use --speed 1.0")
    from cloud_tts import synthesize
    return synthesize(text, voice, _GOOGLE_ACCENTS.get(voice, "US"))


_GOOGLE_ACCENTS: dict[str, str] = {}


def _rendered(result):
    """Accept either ``(audio, segments)`` from render_kokoro or a bare audio sequence."""
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], list):
        return result[0], result[1]
    return result, None


TURN_GAP = 0.18


def solo_sections(body: str) -> list[str]:
    return [paragraph.strip() for paragraph in re.split(r"\n\s*\n", body.strip()) if paragraph.strip()]


def narration_inputs(transcript: dict, cast: dict, voice_key: str = "voice") -> list[dict]:
    """Preflight every turn before synthesis; never silently drop a speaker/show."""
    host = transcript["host"]
    hosts = dialogue_hosts(host)
    if hosts:
        validate_dialogue_contract(transcript["draft"], transcript["source"], hosts)
        inputs = turns_narration_inputs(transcript["draft"], hosts)
    else:
        validate_podcast(transcript["draft"], transcript["source"], HOSTS[host])
        # Preserve editorial paragraph breaks as acoustic scene boundaries.
        inputs = [{"host": host, "text": paragraph}
                  for paragraph in solo_sections(transcript["draft"]["body"])]
    report = transcript.get("verification") or {}
    if report.get("pass") is not True:
        raise ValueError(f"{transcript['show']}: script has not passed evidence verification")
    if report.get("draft_sha256") != draft_fingerprint(transcript["draft"]):
        raise ValueError(f"{transcript['show']}: verification is stale; reverify the edited script")
    # Audience review is a separate gate, checked here because rendering is a release
    # boundary. A missing, stale or failed report is never a pass.
    listener = transcript.get("audience") or {}
    relaxed_revise = (os.environ.get("LILT_ENTERTAINMENT_RELEASE") == "1"
                      and listener.get("decision") == "revise"
                      and listener.get("beat_fit") in ("grounded", "weak"))
    if listener.get("pass") is not True and not relaxed_revise:
        raise ValueError(f"{transcript['show']}: script has no passing audience review; "
                         "run `pipeline.py audience <id>` and repair the failures")
    if not audience.is_fresh(listener, transcript["draft"]):
        raise ValueError(f"{transcript['show']}: audience review is stale for this script, "
                         "contract or review version; re-review before rendering")
    for item in inputs:
        voice = (cast.get(item["host"]) or {}).get(voice_key)
        if not voice or not item["text"].strip():
            raise ValueError(f"Missing voice or text for {item['host']}")
        item["voice"] = voice
    voices = [cast[h]["voice"] for h in dict.fromkeys(i["host"] for i in inputs)]
    if len(voices) != len(set(voices)):
        raise ValueError("Each presenter must have a distinct voice")
    return inputs


def render_turns(inputs: list[dict], wav: Path, speed: float, render=None,
                 sound_design: SoundDesign | None = None) -> list[dict]:
    """Write mono PCM and align each paragraph's words to its own audio."""
    import array
    import math
    render = render or render_kokoro
    paragraphs, offset = [], 0
    with wave.open(str(wav), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(SR)
        if sound_design:
            intro = sound_design.intro()
            stream.writeframes(intro.tobytes())
            offset += len(intro)
        for index, item in enumerate(inputs):
            audio, segments = _rendered(render(item["text"], item["voice"], speed))
            if len(audio) == 0 or not all(math.isfinite(float(v)) for v in audio):
                raise ValueError("Narration returned empty or non-finite audio")
            if index:
                bridge = sound_design.between(index, len(inputs)) if sound_design else None
                if bridge is not None:
                    stream.writeframes(bridge.tobytes())
                    offset += len(bridge)
                else:
                    gap = round(TURN_GAP * SR)
                    stream.writeframes(b"\0\0" * gap)
                    offset += gap
            words = item["text"].split()
            aligned = align.align(words, audio, SR, segments=segments)
            paragraph = {"words": [{"text": word["text"],
                                    "start": round(offset / SR + word["start"], 3),
                                    "end": round(offset / SR + word["end"], 3)}
                                   for word in aligned]}
            if "speaker" in item:
                paragraph.update(speaker=item["speaker"], hostID=item["host"])
            paragraphs.append(paragraph)
            pcm = array.array("h", (round(max(-1, min(1, float(v))) * 32767) for v in audio))
            if sys.byteorder != "little":
                pcm.byteswap()
            stream.writeframes(pcm.tobytes())
            offset += len(audio)
        if sound_design:
            stream.writeframes(sound_design.outro().tobytes())
    return paragraphs


def main() -> None:
    global _GOOGLE_ACCENTS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcripts", required=True, help="a full-run transcripts directory")
    parser.add_argument("--out", default=str(ROOT / "ios/Zwicky/Episodes"))
    parser.add_argument("--voices", default=str(ROOT / "tools/tts/voice_cast.json"))
    parser.add_argument("--date", default="")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--tts-provider", choices=("kokoro", "google-cloud"), default="kokoro")
    parser.add_argument("--require-all-shows", action="store_true", help="fail before rendering unless all 16 shows are present")
    args = parser.parse_args()

    import datetime as dt
    published = args.date or dt.date.today().isoformat()
    cast = load_cast(Path(args.voices))
    voice_key = "geminiVoice" if args.tts_provider == "google-cloud" else "voice"
    if args.tts_provider == "google-cloud":
        _GOOGLE_ACCENTS = {entry["geminiVoice"]: entry.get("accent", "US")
                           for entry in cast.values() if entry.get("geminiVoice")}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    legacy = sorted(p.stem for p in out.glob("*.json") if p.stem != "index")

    jobs = []
    for path in sorted(Path(args.transcripts).glob("*.json")):
        transcript = json.loads(path.read_text())
        jobs.append((transcript, narration_inputs(transcript, cast, voice_key=voice_key)))
    if not jobs:
        raise ValueError("No transcript artifacts found")

    if args.require_all_shows:
        expected = {host.show for host in HOSTS.values()}
        actual = {transcript["show"] for transcript, _ in jobs}
        if actual != expected:
            raise ValueError(f"Incomplete show batch: missing {sorted(expected - actual)}, unknown {sorted(actual - expected)}")

    rendered = []
    for transcript, inputs in jobs:
        name = episode_key(published, transcript.get("doi", ""), transcript["show"])
        wav = out / f"{name}.wav"
        print(f"rendering {transcript['show']} -> {name} ({len(inputs)} turns) ...", flush=True)
        sound_design = SoundDesign(name)
        renderer = render_google_cloud if args.tts_provider == "google-cloud" else render_kokoro
        paragraphs = render_turns(inputs, wav, args.speed, render=renderer, sound_design=sound_design)
        duration = wav_duration(wav)
        payload = story_for(transcript, duration, published, episode=name, paragraphs=paragraphs)
        payload["audioDesign"] = {"stingerSHA256": sound_design.fingerprint,
                                  "assets": ["Kenney Interface Sounds (CC0)", "Kenney Music Jingles (CC0)"]}
        payload["levels"] = envelope_wav(wav)
        to_m4a(wav, out / f"{name}.m4a")
        wav.unlink()
        (out / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False) + "\n")
        print(f"  {duration:.1f}s, {len(payload['levels'])} level frames", flush=True)
        rendered.append(name)

    index = sorted(set(legacy) | set(rendered))
    (out / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(f"bundled {len(rendered)} episode(s); index has {len(index)}")


if __name__ == "__main__":
    main()
