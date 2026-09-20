#!/usr/bin/env python3
"""Generate Zwicky host-voice samples with Kokoro-82M (Apache-2.0). No API key.

Kokoro ships fixed voicepacks (no cloning, no consent questions) and is
Apache-2.0 for both code and weights. This assigns each of the 20 presenters a
distinct English voice from tools/tts/voice_cast.json.

    pip install kokoro soundfile        # Linux also: apt-get install espeak-ng
    python tools/tts/kokoro_generate.py --host fern --out tts-out
    python tools/tts/kokoro_generate.py --out tts-out          # every host

Voice prefixes pick the pipeline: a = American English, b = British English.
Output is 24 kHz.
"""
from __future__ import annotations
import argparse
import json
import os


def load_pipelines():
    from kokoro import KPipeline
    return {"a": KPipeline(lang_code="a"), "b": KPipeline(lang_code="b")}


def say(text: str, voice: str, out_path: str, pipelines, speed: float = 1.0) -> None:
    import numpy as np
    import soundfile as sf
    language = "b" if voice.startswith("b") else "a"
    chunks = [audio for _, _, audio in pipelines[language](text, voice=voice, speed=speed)]
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    sf.write(out_path, np.concatenate(chunks), 24000)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", default="")
    parser.add_argument("--voice", help="a Kokoro voice id (single render)")
    parser.add_argument("--host", help="a host id from the cast (single render)")
    parser.add_argument("--cast", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_cast.json"))
    parser.add_argument("--out", default="tts-out")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--max-words", type=int, default=0)
    args = parser.parse_args()

    cast = json.load(open(args.cast, encoding="utf-8"))
    cast = {k: v for k, v in cast.items() if not k.startswith("_")}

    jobs = []
    if args.voice:
        text = args.text or "This is a Kokoro voice sample for Zwicky."
        jobs.append(("voice", args.voice, text))
    elif args.host:
        entry = cast[args.host]
        jobs.append((args.host, entry["voice"], args.text or entry["line"]))
    else:
        for host, entry in cast.items():
            jobs.append((host, entry["voice"], args.text or entry["line"]))

    if args.max_words:
        jobs = [(h, v, " ".join(t.split()[:args.max_words])) for h, v, t in jobs]

    pipelines = load_pipelines()
    for host, voice, text in jobs:
        out_path = os.path.join(args.out, host + ".wav")
        count = len(text.split())
        print(f"{host}: voice={voice} words={count}", flush=True)
        say(text, voice, out_path, pipelines, speed=args.speed)
        print("saved", out_path, flush=True)


if __name__ == "__main__":
    main()
